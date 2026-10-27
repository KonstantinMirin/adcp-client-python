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
second one: `X is Y` holds, and the surface exports it once. **That carve-out reaches across
modules as well as inside one (2026-10-26)**, because a document that is a bare `$ref` to another
document states the same node, and §4's rule for the same node stated twice does not change at a
file boundary. Where the target is a class the root is a subclass of it instead, which is one
class per name and needs no carve-out at all; the identity binding is for a target that is an
alias, an enumeration or a root model, where there is nothing to subclass.

**Every portable document of the bundle contributes a symbol** — a class, a root model, an
enumeration or an alias — because §2 admits no document without one.

The bundle directory is an argument (`python -m codegen.emit --bundle <dir>`). Nothing reads a
hard-coded path, so a second bundle version can be generated beside the first.

---

## 2. Design principles

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

*Why every one.* Naming only the shapes that recur needs a census over the run, and a census
makes one document's module a function of which other documents the run includes: a run over
one document and a run over the bundle would emit different text for the same document. A name
that is a function of the constraint alone has no such coupling, and the cost — a name for a
shape stated once — is a name a reader can derive from the constraint it spells.

### Rules are after-validators, written once

A keyword that spans fields, or spans a collection, has no field-level annotation that can carry
it. Those become rules: an after-validator in `src/adcp/types/_runtime.py` reading a class-level
tuple the emitter writes. The families are `oneOf`/`anyOf` over `required` or over pinned
values, `if`/`then`/`else`, `dependencies`, `minProperties`/`maxProperties`, `uniqueItems`,
`not`, and `contains`.

**Where a rule hangs:** on the nearest class if there is one, because a class can read sibling
fields. Where no class sits above the value — a root array, a mapping value, a `definitions`
entry, a union branch — the rule hangs off the value's own annotated type as an after-validator
(`AtLeastOne`, `NotValue`, `Distinct`).

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

*Why.* A rewriting pass is a second source of truth for the output's shape, and the two drift. It
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

**This replaces "a keyword we cannot express refuses the document", decided by the owner on
2026-10-26:** *"We accept ZERO refusals as an outcome in the scope of this work. Every single
schema should be represented as a Python class. And if it can't — then we look into the reasons
and approximate it, and raise the upstream issues."*

What it replaced said: where a position carries a keyword we have no compilation for, the
document is refused by name, pointer and keyword, and is not emitted — because "a partial model
is worse than none: it would claim conformance to a document it does not enforce."

*Why it is replaced: that sentence contradicts the first principle of this section.* The first
principle says the model is not the authority on acceptance — `strict_validate` runs the
document before anything is constructed, and the document decides. A model looser than its
document therefore claims nothing it does not enforce, because the claim is not the
annotation's to make: the schema half has already refused the payload. "It would claim
conformance" presumes the annotation IS the conformance claim, which is the proposition the
first principle denies. The two cannot both stand, and the first is the one every other
decision in this document rests on. The widened annotation costs **static precision**, not
runtime correctness, and the refusal was paying a document's whole typed surface for it.

The refusal argument survives in exactly two places, and the design keeps both.

- **A narrowing.** An annotation tighter than its document refuses a payload the protocol
  permits, and `strict_validate` cannot repair it: the schema half admits the payload and the
  construction then fails. A narrowing is the defect the old sentence was reaching for, and
  nothing below widens into one.
- **No document of record.** Where the record (§3) is undefined, there is no schema half at all,
  so `strict_validate` has no authority to run and the annotation is the only claim there is.
  That is the one case where a partial model really would claim conformance to a document it
  does not enforce, and it is the one refusal this compiler can still mint. §7 names its three
  shapes and says what each is measured at.

#### Direction: every approximation of acceptance is a widening

A fact the annotation cannot carry is **dropped**, never substituted. Dropping a constraint
widens the admitted set and can do nothing else; substituting a "nearest expressible"
constraint could narrow, so substitution is not available. The handler takes the lowest rung of
one ladder it can render, and the ladder is finite, monotone and terminates:

1. **KEYWORD** — drop the one keyword, keep the type. (`uniqueItems` where no class and no
   named type hold the rule → `list[X]`.)
2. **TYPE** — drop a type selection the constraints contradict, keep the constraints.
   (`format: uri` beside `maxLength` → the constrained `str`, the format riding as
   `json_schema_extra`.)
3. **JOIN** — replace a shape with the union of the shapes it holds. (A list-valued `items` →
   `list[A | B | …]`, dropping position and arity.)
4. **CONTAINER** — replace the node with its bare container: `list[Any]`, `dict[str, Any]`.
5. **TOP** — `Any`.

`Any` admits everything, so the ladder always has a rung left and no node can run out of
renderings. **Which rung a keyword takes is the keyword's decision and lives in its cell
(§5), never at the site that widens.**

A narrowing is not discouraged here; it is a **failing check**. §8's accepts draw covers the
node's admissible space by constraint class, so a type that refuses any value the document
admits is reported with the value. Where a widening would still leave a narrowing — the type
word itself refusing what a constraint admits — the type widens by another rung, to `Any` if
nothing else carries it.

#### An approximation is declared, and it is local

A refusal propagates: a parent returns it upward unchanged and the document emits nothing. An
approximation does **not**. It is a property of one node, the document still emits, and the
approximation travels upward only to be **accumulated** — a refusal is absorbing, an
approximation is additive. Every one carries its document, its pointer, the keyword whose fact
the annotation does not carry, the rung it took, that fact in the document's own spelling, and
an **attribution**. Nothing is approximated by silence: an undeclared widening is a defect and
§8 reports it as one.

#### Two kinds of approximation, and they are never summed

- **WIDENED** — the annotation admits a value the document refuses. The schema half refuses it,
  so acceptance is unharmed; what is lost is what the type says. §8's comparison sees every one
  of these, because the document states a fact the model does not.
- **UNDERDETERMINED** — the annotation admits exactly what the document admits, and the VALUE it
  constructs is not determined by the document. The only instance is a union whose branches
  §4's dispatch cannot separate: `A | B` accepts the union of the branches either way, and
  which branch an overlapping payload becomes is then a property of declaration order. No
  comparison, draw or dump can see one, which is precisely why it is declared and why its
  instrument is different (§8).

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

- **Emitted, over the population.** Every portable document of the bundle emits, and its
  complement is the one irreducible class above — no document of record. This is a partition and
  it is the directive's exit condition: *refused* is zero.
- **Defects, over the facts compared.** *Missing*, *differs*, *added* and *over-declared* are
  each pinned at zero.
- **Approximations, over the facts compared**, split by kind and by attribution. This count
  moves with emission, so §9 forbids pinning it; it is reported, and its `Ours` half ratchets
  down.

The approximation count is **not** a partition of the population the way *emitted / refused*
was: one document carries many and most carry none. The number of documents carrying at least
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
shape. **Every node reaches a lowering**: the seam is total, because a keyword the handler
cannot render widens the annotation by §2 rather than refusing the document. The one refusal
left is the record's own — a document whose references cannot be inlined has no record, so
there is nothing for the walk to read and nothing for `strict_validate` to validate against.
`Refusal` therefore lives with the bundle reader that mints it, not with the lowerings.

### The document of record

What the walk reads, what `strict_validate` validates against, and what §8 compares against is
one document: the bundle's document with every cross-document `$ref` replaced by a copy of its
target, and **nothing else changed**. Resolution inlines; it does not rewrite. No keyword is
dropped, derived, reordered or restated in another spelling, on the referring node or on the
inlined target.

*Why.* A resolver that canonicalises while it inlines — an `enum` of both booleans for a
`bool`, a `const` for a `null`, a bound derived from a sibling, an annotation dropped — writes a
document the bundle does not state, and every reader downstream then grades the model against
that document instead of the bundle's. A payload generator may canonicalise its own copy in order
to draw from it; that copy is an instrument of one check, and it is not the document.

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
| a `oneOf` / `anyOf` of shapes | a base plus one class per branch |
| a `oneOf` / `anyOf` of scalars at a root | a module-level alias over the union of their types |
| a `oneOf` / `anyOf` at a root mixing a scalar branch with a class branch | a root model over the union of the branches' types |
| a root stating no schema keyword at all | a permissive root model |

A root scalar is an alias, so it has no class to carry `strict_validate`; its module binds the
same validation as a module-level function over the same schema reference, so a class and an
alias cannot disagree about what their document accepts.

**The last two rows are new on 2026-10-26 and each replaces a refusal.**

A root union mixing a scalar branch with a class branch used to refuse by name, on the reasoning
that "the root symbol is a class or an alias, no shape here carries both". A **root model**
carries both: its root type is the union of the branches' types, the scalar branch is a member
type and the class branch is its own class, and the root model inherits `strict_validate` like
any class. Nothing is dropped and nothing widens — the union admits exactly what the document
admits — so this row costs no approximation. What it costs is ergonomics: a consumer writes
`X(root=…)` where a base-plus-branches root takes the payload directly. That is a smaller price
than a document with no type, and the row the old sentence was protecting — an all-scalar root
union, which stays an alias — is untouched.

A root stating no schema keyword at all is a registry's instance data sitting at a schema root,
and §7 used to refuse it. Read by its own declared draft it is the **empty schema**: draft-07
ignores an unknown key, so the document admits every instance, and a permissive root model is
**faithful** to it rather than wide. Refusing it was never a statement about the document's
accepted set; it was how the fact that the document is not really a schema showed up in the
report. That fact now shows up where it belongs — as an approximation at the root with an
upstream attribution, asking the registry either to drop its `$schema` or to declare a schema —
and §7 says why the keyword half of that row is not a refusal either.

Every one of these shapes carries `strict_validate` against its own document by one mechanism,
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
  element, `<Property>Value` for a mapping value, `<Root><Key>` for a `definitions` entry. The
  module path already carries the document, so a nested name does not repeat it.
- **Union branch**: its own `title`; else the `const` it pins on the discriminating property; else
  its sorted `required` set; else its **index among the branches**, `<Base>Branch<i>`.

**The two fallbacks are new on 2026-10-26, and each replaces a refusal with a derivation.** A
missing root title used to refuse, and a branch with no identity used to refuse. Neither is an
acceptance fact: a symbol is not something a document states about an instance, so deriving one
from the document's own path or from its own branch order neither widens nor narrows, and it
costs no approximation. Both fallbacks are functions of the one document — the file stem is the
same whichever documents the run includes, and the branch index is document order — so §9's rule
against deciding a document's output by a census over the run holds. A title is still preferred
wherever one exists, because a derived name reads worse; what changes is that its absence is no
longer fatal.

### A union root: the base, the branches, and how a payload reaches its branch

A `oneOf`/`anyOf` root emits a **base** carrying `BranchDispatchMixin` plus **one class per
branch**, and the base's name is what every referrer imports. A branch whose schema is a `$ref` is
a class with **two bases**: the target, which supplies the fields, and the union's base, which
supplies the dispatch.

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

  *What that schema is, settled 2026-10-27, because the sentence above admits two readings and
  both lose data.* Read as "the base's own plain schema, alone", a BRANCH reached through a
  base-typed field serialises as the base's fields and the branch's own are dropped silently —
  measured, it comes back as `{"shared": null}`. Read as a union of the branches plus that
  schema, a BASE instance matches no arm under a smart union and the serialiser falls through to
  the circular reference the mechanic exists to avoid. Both readings were live: the second is
  what the code does, and it became reachable for the first time at §14 step 9, because while a
  root declaring `properties` was refused every base had no fields and matched the plain arm
  trivially.

  **The serialiser dispatches on the instance's own class, and each class serialises through its
  own plain model schema.** A branch serialises the branch's fields; a base serialises the base's.
  That is not a union in the serializer slot at all, which is why it terminates — there is no
  arm to fail to match and nothing to infer. It also states the obvious invariant the two
  readings each broke in one direction: **a value serialises as what it is.** A base instance is
  a legitimate value, because `__new__` covers `Base(**data)` and validates it, so the slot owes
  it an answer rather than treating it as unreachable.

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

**Every keyword beside the combinator compiles onto the base, and every branch inherits it.**
Draft-07 applies a root's `properties`, `required`, `additionalProperties`, `allOf` and rule
keywords to the same instance a branch describes, so they compile as they would on any class —
fields, `extra`, bases, rules — onto the base, and a branch composes its own with them. A root
`properties: {}` beside a union declares no field and contributes nothing. §8 says how a branch
class is then compared: against its branch node read under the root's siblings, so an inherited
field is a fact the branch's node states.

**Which branch a payload is, is derived from bundle data, never from a hand-written map.** Three
sources, in order:

1. **A `const` every branch pins on one shared property.** The union carries
   `Field(discriminator=<property>)` and the key alone selects the branch, so Pydantic reports
   against that branch rather than against all of them.
2. **A key the bundle's manifest states.** `manifest.task_result_resolution` names the
   discriminator field and a template resolving a schema from it, and `manifest.tools` is the
   table. Such a union emits as a mapping keyed by that field: its discriminant is in the
   envelope, not in the payload.
3. **Branches no instance satisfies twice.** Where the branches are pairwise disjoint, the
   payload selects its own branch and the order they are tried in cannot change which one it
   reaches. Disjointness is derived from the branches themselves: one property pinned to
   different `const` values, a `required` name one branch declares and another forbids, or
   scalar branches of different `type`. A pair the derivation cannot separate is treated as
   overlapping, because admitting a union on an unproven disjointness is the defect this source
   exists to avoid.

A union matching none of the three emits a plain `A | B` over its branches and **declares an
UNDERDETERMINED approximation at the union's pointer, attributed upstream.**

*This replaces a refusal on OVERLAP, 2026-10-26.* The old sentence said a branch is never chosen
by trying each and keeping the first that validates, because overlapping branches make that
answer a property of declaration order rather than of the payload — and that reasoning is
unchanged and is exactly what the approximation now records. What changes is that the
order-dependence is no longer worth a document. `A | B` admits the union of the branches, which
is what the document admits, so **nothing widens and nothing narrows**; for `oneOf` the schema
half still enforces exclusivity, as it already does for every nested union. The whole of the
loss is that an overlapping payload's branch is decided by declaration order, and the document
does not say which branch it should be. That is the UNDERDETERMINED kind of §2, and it is the
only instance of it.

The attribution is upstream because a union whose branches are not separable is a defect in the
union: the bundle already writes the idiom that separates them — each branch forbidding a name
the other requires — so the fix is a copy from elsewhere in the same bundle, and the issue says
so. Where nothing overlaps there is no order to depend on and no approximation, which is why the
third source is a dispatch and not a relaxation.

A hand-written map per document is still not a dispatch source: it is complete with respect to
itself, so a branch added upstream leaves it silently wrong — and unlike declaration order it
would be wrong without saying so, where an approximation says so by construction.

---

## 5. How each keyword compiles

The draft-07 keywords the bundle uses. An answer is given per position where the positions differ.

**The grids in this section are generated from `codegen/keywords.py` and are the cells as they
stand before §2's widening rule lands.** Every clause reading "→ refused" in them is a decision
§2 replaced on 2026-10-26, and the cell that carries it has not yet been rewritten. *"The
widening each row takes"* at the end of this section is the hand-written half and states the cell
each such row takes; the generator writes those sentences into the grids when the cells change,
and until then the grids and that subsection are read together. Nothing hand-edits a grid: a cell
is the one place a keyword decision lives, and a grid is its rendering.

### Structure

<!-- generated from codegen/keywords.py -->
| keyword | compiles to |
| --- | --- |
| `type` | A scalar word → `str` / `int` / `float` / `bool`, unless a constrained type or `format` selects one. `object` with `properties` → a class; without → `dict[K, V]`. `array` → `list[X]`. `null` → `None`. A LIST of words → `A \| B`, each sibling keyword going to the one type word that can carry it. Absent → `Any`; absent beside `properties` → an object, where an enclosing node applies `type: object` to the same instance, and refused otherwise. |
| `properties` | A class with one field per key. ROOT beside a union → fields on the base, inherited by every branch. PROP / ELEM / MAPV / DEF → a nested class. BRANCH → the branch class. CONJ → fields of the composed class. A property two conjuncts declare is one field: its constraints intersect by §2, and two object declarations compose as an `allOf` of the two at that property; an empty intersection — two type words, disjoint enums — refuses, because the document admits nothing there. A `default` or a `description` is not a constraint, and the document's own statement wins over a base's. RULE: under `if` → the values a `Match` clause tests, read only where `const` or `enum`; under `then` / `else` / `not` → nothing. |
| `required` | The named fields are required: no `\| None`, no default. Naming a property no node declares → refused, a presence rule with no field. `required: []` → nothing. ROOT beside a union → required on the base's fields, and the names recorded in `_ROOT_REQUIRED`, so a refusal can separate a field the root requires from one that selects a branch. BRANCH → the branch class's requiredness, and the third of the branch-naming choices. CONJ → unioned into the composed class's `required`; a `required`-only conjunct → the overlay. RULE → a presence rule: `RequiredGroups`, `ForbiddenGroups` under `not`, the keys a `Match` clause tests under `if`, `ConditionalRequired` / `NegatedConditional` under `then` / `else`. |
| `definitions`, `$defs` | Nothing by itself: a bag of named subschemas. Each entry is declared on demand when a `$ref` names it, as the node's own kind, under `<Root><Key>`. |
| `$ref` | Another document's root → an IMPORT of that module's symbol; nothing of the target is copied into the module, and in the document of record (§3) the target is inlined unchanged. A fragment of another document → an import of a symbol the target declares. Local `#/…` → the entry decided on demand in this module; a cycle refuses. An annotation sibling → the sibling's description wins. A CONSTRAINING sibling → nothing, and REPORTED: draft-07 ignores every sibling of `$ref`, so the keyword constrains no instance and the document's accepted set is the target's alone. The record keeps the key, because §3 drops none; the declaration's cell says it compiles to nothing at this co-occurrence, so §8 does not grade it; and the report names it, because a key that reads as a constraint and is inert is worth reading once. Refusing it instead would refuse a document whose accepted set its own draft decides, and letting the referring value win would make the record state an acceptance fact the bundle does not — §9's last rule. KEY → the key type. BRANCH of a root union → a class with two bases; of a nested union → a member type. CONJ → a BASE where the target is a class declaring fields. Where it is not — a scalar, an enum, a container, or a union root, whose instance is one of its branches — it is not a class a model can extend: the target is this node's own TYPE, and the other conjuncts and the `allOf`'s siblings constrain it, which is §2's intersection at a node that declares no fields of its own. |
<!-- end generated -->

### Values

<!-- generated from codegen/keywords.py -->
| keyword | compiles to |
| --- | --- |
| `const` | `Literal[value]`; the type word is not restated, since Pydantic renders it. A `str`, `bool` or `int` value; an object, array, `null` or float refuses. On a branch's property → also the second of the branch-naming choices. AT a branch node, pinning the whole branch → the branch is a scalar: a `Literal` member of the union. Where EVERY branch of a root union is a scalar there are no branch classes to declare, so the root emits as an alias over the union of their types — `Literal['asap'] | AwareDatetime` — and not as a base with branches. A root union with a scalar branch beside a class branch → refused by name: the root symbol is a class or an alias, no shape in §4 carries both, and the first document to state one decides it rather than taking a rendering nothing has exercised. RULE: under `if` → a `Match` clause's value; under `then` / `else` / `not` → nothing. |
| `enum` | A named node → `StrEnum` / `IntEnum`, base read off the members; `enumDescriptions` → member docstrings. An untitled BRANCH of a root union → a `Literal` of the members. Mixed member types, an empty list, or a duplicate member → refused. Two members whose spellings yield one Python name → refused, naming both: a silent collision would drop a member the document admits. ROOT → the enum with a module-level `strict_validate`. PROP → a nested enum. KEY → a `Literal` of the members as the mapping's KEY type, which pydantic renders back as `propertyNames: {enum: […]}` — the document's own keyword, rendered and gradable; where the key node carries a `title` the `StrEnum` is the key type and renders the same way. RULE: under `if` → `Match` values; else nothing. |
| `default` | On a REQUIRED property → dropped and reported, because no rendering makes a field both required and defaulted. On a node that becomes an alias → no slot. PROP → the field's default; `None` is a default, absence is not. |
<!-- end generated -->

### Strings

<!-- generated from codegen/keywords.py -->
| keyword | compiles to |
| --- | --- |
| `pattern` | `pattern` on the type, as a named alias. On `format: uri` → selects the type instead, and the pattern stays with the schema half. The regex engine is derived per class, because a pattern using look-around needs Python's engine rather than Rust's. ROOT → the root alias over it. ELEM / BRANCH → the alias as the element or member type. KEY → an annotated `str` key. RULE → nothing. |
| `format` | Selects a TYPE where the document's draft asserts the format and a type is named: `date-time` → `AwareDatetime`, `date` → `datetime.date`, `uri` → a URL type chosen by `pattern`. Otherwise rides as `json_schema_extra={"format": …}` on the field. A `uri` beside another string constraint → refused: a URL type carries none. ELEM / MAPV with no type selected → a named alias carries it. BRANCH → the selected type as the member. |
| `minLength`, `maxLength` | `min_length` / `max_length` on the type, as a named alias. On a URL type → refused, not representable. ROOT → the root alias. ELEM / MAPV → the alias inside the container. KEY → the key type, which Pydantic renders back as `propertyNames.minLength`. RULE → nothing. |
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
| `minItems`, `maxItems` | `min_length` / `max_length` on the annotation of the **array's own type**, at every position. `minItems: 0` states nothing. `constraints` declares it once, generically, as `type NonEmptyList[T] = Annotated[list[T], Field(min_length=1)]`. PROP → on the field. ELEM / MAPV / DEF → the container's type must be named to carry it. BRANCH → on the branch's own type, never on the field holding the union. RULE → nothing. |
| `uniqueItems` | A `UniqueItems` rule on the class holding the array, plus `json_schema_extra={"uniqueItems": true}` on the field so it is graded, and the keyword is stripped off the array's own declaration. Where no class sits above the array → a `Distinct` after-validator on its own annotated type, beside the same `json_schema_extra`. |
| `contains` | An existential quantifier — `items` constrains every element, `contains` says at least one matches — and the model states the **predicate**, not a transcription of the subschema. A field position → an `AtLeastOne` after-validator on the array's own annotated type: `AtLeastOne(**{property: const})` where the subschema requires properties pinned to a const, `AtLeastOne(value)` where it is a bare `const` or a one-member `enum`. Any other predicate at a field position — a bound, a pattern, a nested `contains`, a `$ref` — → refused by name: a transcription of the subschema is the thing this row declines to emit, and the first document to state such a predicate decides its rendering. RULE position → a `Match` MEMBERSHIP clause, `value in field`, and no validator. |
<!-- end generated -->

### Objects

<!-- generated from codegen/keywords.py -->
| keyword | compiles to |
| --- | --- |
| `additionalProperties` | The empty schema `{}` IS `true` and is read as `true` everywhere below, never as a typed value schema. On a class: `false` → `forbid`; `true` → `allow`; typed → `allow` with a typed `__pydantic_extra__`; absent → `ignore`. On a mapping (no `properties`) → the VALUE type; `true` or `{}` → `Any`; `false` → refused, it admits only the empty object. Beside `patternProperties` → refused, two value schemas. `false` on an `allOf` overlay would reject the fields its sibling conjunct contributes, which is why `true` is the only value an overlay can carry. ROOT beside a union → the same, on the base, inherited by every branch; a branch stating its own composes with it by the CONJ rule below. CONJ → `true` is the identity and contributes nothing, `false` on any conjunct closes the composed object, and two typed ones intersect their value schemas; a typed conjunct beside a `true` one is a widening and refuses. |
| `patternProperties` | A mapping whose KEY carries the pattern: `dict[Annotated[str, StringConstraints(pattern=…)], V]`, which Pydantic renders back as `patternProperties` — the document's own keyword. More than one pattern → refused: that is a value schema per key shape. Beside a non-`false` `additionalProperties` → refused. |
| `propertyNames` | The mapping's KEY type: a `$ref` → that type; `minLength` / `maxLength` → a length-bounded `str`; `pattern` → an annotated `str`; `enum` → a `Literal` of the members, which pydantic renders back as this very keyword; `anyOf` → a union of key types. Beside `patternProperties` → the key type carries both, by §2's intersection: each states a constraint on the same key. On a CLASS with declared `properties` → checked against the declared names when the class is emitted and carried nowhere, because those names are fixed and known; a declared name the constraint refuses is a contradiction in the document and refuses by name. Where that class also admits extras, a key beyond the declared names is checked by the schema half alone, and the model is looser than its document there, which §2 permits. RULE position → nothing on the model: a rule position constrains which keys a conditional *tests*, so there is no key type to annotate and no value to hang a validator on. |
| `minProperties`, `maxProperties` | On a class → a `PropertyCount` rule. `minProperties` is written only where `additionalProperties` is stated, because a dropped key would make the rule refuse what the document accepts; `maxProperties` needs no such gate, since a dropped key only lowers the count. On a mapping → `Field(min_length / max_length)` on the dict's type, because a `PropertyCount` rule counts declared fields and a dict has none. |
| `dependencies` | The list form → a `Dependencies` rule: if A is present, B is required. The schema form refuses by name on the first occurrence, rather than being skipped. |
<!-- end generated -->

### Combinators and conditionals

<!-- generated from codegen/keywords.py -->
| keyword | compiles to |
| --- | --- |
| `allOf` | ROOT with no union beside → `$ref` conjuncts are BASES, inline conjuncts are fields and rules of this class; beside a union → the same, onto the base: `$ref` conjuncts are the base's bases and inline conjuncts are its fields and rules, and every branch inherits them. PROP / ELEM / DEF → the same reader at the node's own pointer. BRANCH → the branch class composes, with the union base first. CONJ → the same rule applied to the conjunct's own conjuncts. RULE: under `not` → single-group conjuncts merge into one group; else nothing. |
| `oneOf`, `anyOf` | Presence-only, every branch `required`-only → a `RequiredGroups` rule naming the combinator. Presence-only where a branch also `not`s a group of `required` → a `PresenceGroups` rule naming the combinator, whose clauses are the branches: each clause carries its OWN required group and its own forbidden groups, because the `not` is per branch — a `ForbiddenGroups` over the union of them forbids every group unconditionally and refuses a payload the document admits. Shapes at ROOT → the base plus one class per branch. Shapes nested → one type `A \| B`; a sibling beside it refuses. For `oneOf`, `A \| B` admits an instance satisfying two branches and the schema half enforces exclusivity. A union whose branches declare the same properties with the same `required`, and differ only in the `const` or `enum` each pins on some of them → one class: each such field admits the union of the branches' values, and one rule whose clauses are the branches themselves — one clause per branch pinning that branch's values, satisfied when the instance matches at least one clause. A branch that differs in a type, a bound, a format, a nested shape or its `required` is a branch of shapes and takes the base-plus-branches answer. For `oneOf` the schema half enforces exclusivity, as it does for `A \| B`. KEY → a union of key types. CONJ → one class per branch over the composed bases. RULE: under `not` → the union of the branches' groups; else nothing. |
| `if` | A `Match` clause list where it states `required` plus `properties` with `const` or `enum` values; otherwise nothing, and the schema half answers. With `then` / `else` → a rule on the nearest class. |
| `then`, `else` | `ConditionalRequired` / `NegatedConditional` from its `required` and a single-name `not`. Its `properties` → nothing on the model; the schema half narrows the value. |
| `not` | `not: {required: …}`, and `anyOf` / `allOf` of those → a `ForbiddenGroups` rule. Over a `const` or `enum` → a `NotValue` after-validator on the value's own annotated type. Any other shape → nothing on the model; the schema half answers and the ceiling is named. `not: {}` admits nothing, which the typeless `Any` carries. |
<!-- end generated -->

### The widening each row takes

Every "→ refused" clause above becomes one of three answers, and **the largest group is neither
a refusal nor an approximation.** The rows sort as follows.

**(a) Rows whose answer is already decided here and was never implemented.** These cost no
approximation at all: the sentence that grades them exists, the compiler does not honour it, and
the directive's first effect is to make it. They are the dominant class.

- **A plain keyword beside a `oneOf` / `anyOf`.** §4's union section already decides it — "every
  keyword beside the combinator compiles onto the base, and every branch inherits it" — and §8
  already decides how the result is graded, against the branch node read under the root's
  siblings. The refusals reading "there is no pointer to the conjunction for it to name" predate
  that pairing rule and are answered by it. No widening; the keyword compiles.
- **`propertyNames` with an `enum`, and `enum` at KEY.** Both rows refuse "by name with the key
  set". A `Literal` of the members is the key type, and Pydantic renders `dict[Literal[…], V]`
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
- **A root that is a bare `$ref`.** Refused because binding this module's symbol to another
  module's class would be a second way to reach one class, against §1. Where the target is a
  class the answer is a **subclass** of it, which is one class per name and accepts exactly what
  the base accepts, so §1 is untouched. Where the target is an alias, an enumeration or a root
  model there is nothing to subclass and the symbol is bound to the target **by identity**, which
  §1's own carve-out already admits inside a module and now admits across one: `X is Y` holds and
  the domain surface exports it once.
- **A scalar, enum, container or union target as a conjunct of an `allOf`.** The `$ref` row
  already decides it — "the target is this node's own TYPE, and the other conjuncts and the
  `allOf`'s siblings constrain it" — and the refusals reading "*X* is not a class, so it cannot
  be a base" are the unimplemented half of that sentence.
- **`uniqueItems` and `contains` where no class holds the value.** §2 already decides it: where
  no class sits above the value, the rule hangs off the value's own annotated type. A root array
  is a root model, and a root model carries a rule tuple exactly as a class does, so `Distinct`
  and `AtLeastOne` reach it. The keyword is enforced, not dropped.
- **A root stating only `if` / `then`.** Refused because "a root is exactly one kind and this one
  states `if`". The conditional is a rule, and §2 hangs a rule with no class above it on the
  value's own type: the root is a permissive root model carrying `ConditionalRequired`. The
  document states a conditional and nothing else, and so does the model.

**(b) Rows whose answer is a declared widening.** Each names its rung (§2's ladder) and its
attribution.

- **`uniqueItems` and `contains` where even a named type cannot hold the rule.** Rung KEYWORD:
  the array is `list[X]` and the duplicate or existential check is the schema half's alone.
  Attribution ours. These keywords are RULE-effect, so §8 grades them against the class's rule
  tuple and the approximation is declared against that tuple rather than against a schema fact.
  **`contains` keeps its own refusal of transcription and drops only the document.** The row
  declines to transcribe a `contains` subschema into a validator, and that decision stands —
  what it may no longer do is refuse the document for it. Dropping the keyword widens the array
  (a list with no matching element is accepted by the model and refused by the schema half) and
  transcribes nothing, so the row gets both of the things it wanted.
- **A list-valued `items`.** Rung JOIN: `list[A | B | …]` over the positional schemas, dropping
  position and arity, with the element type collapsing to `Any` where `additionalItems` is
  absent or `true`. **The arity bound is not derived.** `additionalItems: false` implies
  `maxItems: len(items)`, and §3 forbids deriving a keyword the bundle does not state, so the
  bound stays with the schema half and the model does not restate it. Attribution ours.
  Unexercised: bundle 3.2 states no list-valued `items` and no `additionalItems`, so this row
  decides a shape before it arrives rather than after.
- **An `allOf` restatement that neither matches nor narrows.** §2's intersection is the document's
  own accepted set, and the refusal exists where the intersection of two object or two array
  declarations is not computable. Rung KEYWORD: the field takes the base's declaration and the
  restatement's extra facts are dropped. That widens relative to the intersection and cannot
  narrow, because the base is one conjunct and the intersection is a subset of it. Attribution
  ours.
- **An empty intersection** — two disjoint type words, two disjoint enums. The node admits
  nothing, which is a contradiction in the document. Rung TOP, and this is the answer the `not`
  row already gives for `not: {}`: "admits nothing, which the typeless `Any` carries", with the
  schema half refusing every payload. Attribution upstream, because a conjunction admitting
  nothing is a defect in the conjunction.
- **A keyword in none of §5, §6 or §7.** Rung TOP: the node is `Any`. Draft-07 ignores an
  unknown key, so the document may be narrower than `Any` but can never be wider, which makes
  `Any` the one safe rung when the keyword's reach is unknown. §2's by-name principle is intact
  — the key is not silently ignored, it costs a declared approximation at the top rung and a loud
  report line — and the node losing its whole type is exactly as visible as a refusal was.
  Attribution ours.
- **A union whose branches §4's dispatch cannot separate.** The one UNDERDETERMINED row; §4 states
  it.
- ~~**A root stating no schema keyword.**~~ **Moved to (a) on 2026-10-26: it is faithful and
  carries no declaration.** This row sat here and its own sentence called the answer "faithful to
  a document that admits everything", which is group (a)'s definition and not this group's. A
  permissive root model over a document that constrains nothing DROPS nothing, so there is no
  fact to declare — and §8's *over-declared* outcome would have reported the declaration this
  group asked for, which is the mechanism catching the row rather than a reader having to.
  Measured on `core/asset-group-vocabulary.json`, which declares draft-07 and whose keys
  (`version`, `lastUpdated`, `vocabulary`) are not schema keywords: `Draft7Validator` accepts
  `42`, `"x"`, `null`, an object and an array, so the permissive model is exactly as wide as the
  document. The upstream issue stands — the schema should say more than it does — but **an
  upstream issue is not an approximation**, and filing one is the issue list's job, not a
  declaration's.

**(c) Rows that refuse nothing because there is no fact to approximate.** `errorMessage` and the
registry data keys constrain no instance, so no annotation drops anything for them. They move to
§6 — admitted by name, compiling to nothing, reported — and §7 says what becomes of its own set.

### A union of presence-only branches that also forbid (decided 2026-10-27)

The `oneOf`/`anyOf` row's presence clause reads "every branch `required`-only", and 11 documents
hold a union whose branches constrain presence only and are NOT `required`-only. Row `.20`
measured them as two shapes and this section answered neither. They go to different places, and
the generated cell is written by the row that implements each.

**Group A — every branch is `required` plus a `not` of required groups. This is FAITHFUL, and
it needs one new rule kind.** Six documents: `core/audience-characteristic.json`,
`core/catchment.json`, `core/creative-asset.json`, `core/creative-manifest.json`,
`core/frequency-cap-impression-constraints.json`, `core/frequency-cap-interval-constraints.json`.

Every branch constrains which keys are present and nothing else, so it is a rule on the root's
class and not a branch class. **The answer is ONE rule whose clauses are the branches, each
clause carrying its own required group AND its own forbidden group, with the combinator deciding
how many clauses an instance may satisfy.**

Widening `_required_only` to admit `not` is the obvious move and it is WRONG, measured: the `not`
is per BRANCH, so branch *i* reads "every name in R*ᵢ* present and no group of F*ᵢ* present". A
`RequiredGroups` over the R*ᵢ* beside a root-level `ForbiddenGroups` over the F*ᵢ* forbids every
F*ᵢ* unconditionally — `core/catchment.json` states three methods and forbids the other two per
method, so a root-level rule forbids all three and refuses a payload the document admits. The two
halves must stay paired per clause, and neither `RequiredGroups` (groups and a combinator) nor
`ForbiddenGroups` (groups alone) has a slot for the other half. So `_runtime.py` declares the
new kind and `lower/rules.py` writes it. Nothing is dropped: `APPROXIMATED` does not move.

**Group B — the union MIXES shape branches with presence-only ones. This is a WIDENING, and it
belongs to §14 step 10.** Five documents, among them
`error-details/vast-version-mismatch.json` `/anyOf/2`, `media-buy/buy-products-request.json`
`/anyOf/0` and `media-buy/create-media-buy-request.json` `/anyOf/2`.

A presence-only branch admits ANY object carrying those keys, which is wider than any of the
shape branches' classes. So no type over the shape classes covers the instances the presence
branch admits, and there is no faithful type for the union: the shape branches give classes, the
presence branch gives a rule, and an instance satisfying only the rule is none of the classes.
That is the asymmetry Group A does not have, and it is why the two shapes separate. The fact
dropped is the shape precision of the branches, the type widens by §2's ladder, and the gap is
declared and attributed.

---

## 6. Keywords we admit and do not compile

None of these can constrain an instance, so none compiles to a type, a rule or a base. Each is
admitted **by name**. Several carry something anyway, and the table says what.

**`errorMessage` and the registry data keys join this section on 2026-10-26**, from §7. Neither
constrains an instance — `errorMessage` customises an `ajv-errors` message and the registry keys
are a registry's own instance data — so no annotation drops a fact for them and there is nothing
to widen. They are admitted by name, compile to nothing, and are reported, which is the answer
`$comment` already gets. The grid below is generated and does not yet carry their rows; §7 says
what refusing them was buying and where that now shows up.

<!-- generated from codegen/keywords.py -->
| keyword | what it does, or why nothing |
| --- | --- |
| `$schema` | Nothing on the class, but it selects the **validator** the schema half runs, and through it the format checkers a type may be selected for. The one annotation that decides a behaviour, and it decides it on the schema half. |
| `title` | Nested → nothing: a nested node is named by its property or entry key. Its presence selects `StrEnum` over `Literal` for an enum node. Never rendered. ROOT → the symbol. BRANCH → the branch class's name. |
| `description` | A `$ref` sibling's description wins over the target's; a composed base's loses to the document's own. ROOT class → the docstring; ROOT alias → `Field(description=…)`; ROOT enum → the enum's docstring. PROP → `Field(description=…)`. ELEM / MAPV → the named alias carries it. BRANCH that is a class → its docstring; a non-object branch of a nested union → its own annotated type. CONJ / RULE → nothing. |
| `examples` | Nothing on the model. The accepts check replays every one, at every position: a ROOT example constructs the class, and an example at a nested node is validated against that node's own annotated type. A payload the document refuses is a spec defect, reported by document and pointer; one the document accepts and the class refuses is ours. |
| `$comment` | Nothing. A note to a reader. |
| `readOnly`, `writeOnly` | Nothing. Pydantic can render them, but the SDK has one model per document and no read/write split for them to state. |
| `deprecated` | A `false` → nothing. Rendered, so graded. ROOT / BRANCH → the class's `json_schema_extra`. PROP → `Field(deprecated=True)`. |
| `enumDescriptions`, `x-enum-descriptions` | Member docstrings on the enumeration, keyed by the member's value. Two spellings of one keyword; both are read. |
| `enumMetadata` | Nothing: recovery and action metadata for a reader. The `enum` beside it has already closed the value set. |
| `notes` | Nothing: English sentences for a reader. |
| `discriminator` | Nothing on the class. It names a branch where that branch pins more than one `const`, and separately it **confirms** a dispatch key the branches already state — it does not establish one. A union whose branches pin a distinct const dispatches on that property whether or not the keyword is present, and a declared keyword the branches do not confirm is not a dispatch source. |
| the `x-` namespace | Nothing, and **still listed by name** — see below. |
| `version`, `lastUpdated`, `vocabulary`, and the registry payload keys | Nothing. A registry's own instance data sitting at a schema root: `_generated`, `_generatedAt`, `adcp_version`, `architecture`, `asset_types`, `baseUrl`, `extensions`, `governance`, `last_updated`, `mappings`, `prerelease`, `protocol_layers`, `published_version`, `stability`, `usage_notes`, `versioning`. None of them constrains an instance, and draft-07 says the same thing by ignoring an unknown key, so an annotation that omits one omits no fact and admitting it by name says only what is true of instance data. A root stating only these keys is the empty schema and emits as a permissive root model; a document stating them BESIDE a real schema emits normally, with the data keys compiling to nothing. |
<!-- end generated -->

### The `x-` namespace is admitted by prefix AND listed by name

A vendor extension cannot be a schema keyword, so the `x-` prefix is sufficient to admit one.
That is the one place the by-name principle has an exception — and the exception is leaky, which
is why the names are kept as well: `x-enum-descriptions` carries member docstrings, and the
prefix rule dropped it silently because nothing was looking at the list.

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

**Emptied on 2026-10-26 by the owner's directive (§2).** No keyword's presence refuses a
document. The section stays, with its membership still a projection of the declaration, because
a reader looking for "which keywords refuse" has to find the answer, and because the one
refusal left in the compiler is not a keyword's at all.

Both rows below move to §6. Each was refused for a reason that was never about the document's
accepted set:

- **`errorMessage`** has no Pydantic rendering, and never needed one: it customises a validator's
  message and constrains no instance, so an annotation that omits it omits no fact. The drop is
  reported, as it was.
- **The registry data keys** — `version`, `lastUpdated`, `vocabulary`, `_generated`,
  `_generatedAt`, `adcp_version`, `architecture`, `asset_types`, `baseUrl`, `extensions`,
  `governance`, `last_updated`, `mappings`, `prerelease`, `protocol_layers`, `published_version`,
  `stability`, `usage_notes`, `versioning` — are a registry's own instance data at a schema root.
  The old row's reasoning was that "admitting them by name would be admitting data as vocabulary"
  and that "the documents carrying them are registries rather than schemas, and refusing them is
  how that shows up". The first half was answering a question nobody asked: admitting a key by
  name says it carries no acceptance meaning, which for instance data is simply true, and
  draft-07 says the same thing by ignoring it. The second half was real — the refusal was a
  SIGNAL about the document, not a statement about its accepted set — and a refusal is the wrong
  instrument for a signal, because it costs the document its type to carry it. The signal moves
  to the approximation record: a root stating only these keys is a permissive root model (§4)
  with an upstream attribution asking the registry either to drop its `$schema` or to declare a
  schema. A document that states these keys *beside* a real schema — a `type` and `properties`
  at its root — emits normally, with the data keys compiling to nothing.

**The one refusal the compiler can still mint is not a keyword's.** Where the document of record
(§3) is undefined, there is no schema for `strict_validate` to validate against and no document
for §8 to grade against, so §2's partial-model objection applies with nothing to answer it. The
principle is that **the document has no defined accepted set**, and three shapes reach it:

- a `$ref` whose target is not a bundle document;
- a cross-document reference cycle, which the inliner cannot resolve. A LOCAL cycle is not one
  of these — it is never inlined and renders as a forward reference (§5);
- a document that fails its own declared draft's meta-schema, so it is not a schema at all and
  has no accepted set to be faithful to.

Measured over bundle 3.2's 1,054 portable documents, **all three are empty**: 0 undefined
records, 0 meta-schema failures. That is why "zero refusals" is reachable for this bundle rather
than aspirational, and it is the figure to re-measure on every bundle version. The refusal stays
in the compiler regardless, because a bundle that grows one must report it rather than crash on
it (§9).

<!-- generated from codegen/keywords.py -->
| keyword | why |
| --- | --- |
| `errorMessage` | An `ajv-errors` extension customising a validator's message. It has no Pydantic rendering, and a conjunct carrying one contributes nothing, so the drop is reported rather than silent. |
<!-- end generated -->

The grid above is generated and still carries both rows; the cells move when §6's do.

A keyword in none of §5, §6 or §7 is one the bundle does not use. The first document to carry one
**widens its node to `Any`** — §5's rung TOP — and declares the approximation, so a new keyword
is loud rather than ignored. `Any` and not a narrower rung, because an unrowed keyword's reach is
unknown: draft-07 ignores it, so the document may be narrower than `Any` and can never be wider,
and `Any` is the one rung that is safe without knowing what the keyword does. A node that loses
its whole type is as visible in the report and in the emitted module as a refused document was,
which is what the old sentence was buying.

---

## 8. How we know the output is right

Three checks, run once per emitted class against the schema document it names.

- **Accepts.** Draw payloads the document accepts and construct the class from each. A refusal
  here means the model is tighter than its document, which is the defect that matters.

  **An approximation is a claim about this check, and this check is what proves it.** §2 says
  every approximation of acceptance is a widening. A widening is therefore not a thing a
  declaration asserts and a reader believes: for every fact an approximation drops, the draw
  takes the values that keyword distinguishes — the same coverage classes below — and the class
  must accept every one of them. An approximation that still refuses a value the document admits
  is a NARROWING wearing a declaration, and it fails here, by value and by pointer. This is
  what keeps "approximated" from being an allowlist.

  **The draw COVERS the node's admissible space by constraint class; it does not sample it.**
  "Never tighter" is a claim about every value the document admits, and a sampling draw reports
  only the values it drew — so it can run green forever against a type that refuses a whole class
  of admissible value. For each keyword the node states, the draw takes the classes that keyword
  distinguishes: every member of an `enum`, both sides of each bound and the bound itself, and for
  a `format` every shape the format's own checker admits rather than the shape a generator finds
  most likely. A Python type chosen for a node admits everything the node admits, or the choice is
  a narrowing and this check names it with the value.
- **Dump.** Serialize the instance and validate the dump against the document. A failure means we
  emit something our own schema refuses.
- **Compare.** Compare the class's `model_json_schema()` against the document of record (§3),
  fact by fact. Outcomes are distinguished: a fact both state identically (*matched*), a fact the
  document states and the model does not (*missing*), a fact both state differently (*differs*),
  and a fact the model states and the document does not (*added*). The comparison is symmetric by
  construction, so neither direction can be silently unexamined. It reads the document, never the
  payload generator's canonicalisation of it: a canonicalised view states facts the document does
  not, and a comparison reading it has to undo each of them, fact by fact, to report what the
  document says.

  **A fifth and a sixth outcome, added 2026-10-26 with §2's widening rule.** Under §2 every
  unexpressed keyword widens instead of refusing, so the *missing* bucket would fill with facts
  the design decided to drop, and a grader that cannot tell a decided widening from a defect
  grades nothing. The split is the approximation declaration, read off the emitted class:

  - ***approximated*** — the document states the fact, the model does not, and an approximation at
    that pointer and keyword declares it, names its rung and carries an attribution. Not a
    defect. Counted, listed, and proved wide by the accepts draw above.
  - ***over-declared*** — an approximation is declared at a pointer and keyword where the model
    DOES state the fact. A defect, and the mirror of *missing*. Without it the declarations rot:
    a cell gets written, the widening stops happening, the declaration stays, and it then hides
    the next real gap at the same pointer behind a stale excuse.

  *missing* keeps its old meaning exactly — the document states a compared fact, the model does
  not, and nothing declares it — and it is **the only one of the six that the directive leaves
  as a defect in the undeclared direction.** So the directive does not loosen this check; it
  moves its subject from "is the fact there" to "is its absence declared, attributed and proved
  wide".

  **An UNDERDETERMINED approximation (§2) is invisible to all three checks**, and that is why it
  needs an instrument of its own. The comparison matches, the draw accepts and the dump
  validates, because the annotation admits exactly what the document admits; the only thing
  wrong is that the document does not decide which branch an overlapping payload becomes. Its
  check is §4's disjointness derivation: **the set of unions declaring one equals the set the
  derivation cannot separate**, in both directions, so a union that becomes separable loses its
  declaration and a union that stops being separable gains one.

**The comparison is GENERIC, and its keyword set is DERIVED from one declaration.** One
declaration in the compiler holds every keyword's decision — what it compiles to, and whether the
model renders it as a fact, descends it as structure, enforces it as a rule, or carries nothing.
§5, §6 and §7's tables are GENERATED from that declaration. A test that merely diffs them
against it can compare only what it can parse back out of a table, so a cell deciding one thing
where the text beside it says another passes: generation removes the second copy instead of
checking it. The reasoning in those sections is written by hand and is the part that cannot be
generated; the grids are output. The comparison derives its compared set from the same
declaration: every keyword it renders as a fact. A hand-written list beside the comparison is
the one way this check can be complete with respect to itself and blind to everything beyond
it: a keyword missing from it is unexamined in *both* directions, so the grader cannot tell
whether we rendered it, dropped it, or invented it — and it reports a pass either way.

A keyword the declaration compiles to a rule renders nothing in the model's schema, so the
comparison grades it against the class's rule tuple, which is the fact the emitter wrote for it:
a rule keyword the document states and the tuple does not carry is *missing*, and a clause the
document does not state is *added*.

So two checks stand above the three, and each is an **equality between two sets neither of which
is hand-written**. Nothing else in this section means anything until both hold, because every
other check inherits their reach.

1. **The comparison's keyword set equals the set the declaration renders.** A keyword the
   declaration renders and the comparison does not carry is a defect in the comparison.
2. **The approximated set equals the declared set.** Every *approximated* fact has a declaration
   (or it is *missing*), and every declaration has an *approximated* fact (or it is
   *over-declared*). Both directions, for the reason the first equality has them: a set checked
   in one direction is complete with respect to itself, and what it omits passes.

*Why the second is not a weaker version of an allowlist.* An allowlist is a set a human writes
and a check consults. These are two sets a machine derives — one from the document against the
model, one from the emitter's own record of what it could not render — and the check is that
they agree. Nobody can add an entry to make a failure go away without the model actually
widening at that pointer, because the accepts draw then has to accept the values the keyword
distinguishes. A declaration is a claim with two instruments pointed at it.

**What is pinned, and what is only reported.** §9's rule that a pin with no denominator is not a
ratchet decides this. *Missing*, *differs*, *added* and *over-declared* are pinned at zero: none
of them moves with emission, because each is a disagreement between a model and its document and
a correct emitter produces none however many documents it emits. The approximation count is
**not pinned** — it rises when a document starts emitting, which would oblige every later change
to loosen the pin, the opposite of a ratchet — and is instead reported with its denominator (the
facts compared) and split by attribution, with the *ours* half ratcheting down as §5's cells
land.

*The worked example, which is why the split is necessary rather than tidy.* One keyword's gap —
`deprecated`, rendered by its §6 row and not yet written through — moves *missing* from 0 to 57
facts. Under the directive, without the split, every keyword's gap does that at once and the pin
is abandoned on the first wave. With the split, those 57 are *approximated* against one cell-level
attribution, *missing* stays 0, and the figure that moves is the one that is supposed to move.
A grader whose pin survives the directive is the test of this section, and this is how it
survives it.

Pydantic is deliberately less strict than JSON Schema, so a payload the *document* refuses tells
us nothing about the generated class on either route. There is therefore no "refuses" check on
the model; the equivalent check confirms the schema half is wired to the class at all.

Every class, root model and alias the tree carries is paired with the schema node it names, and
all three checks run over that pairing. **The population every check ranges over is every
portable document of the bundle**, and under §2 every one of them emits, so there is no second
set to reason about: a document that does not appear in the pairing is a defect in the run,
where it used to be a refusal with a reason.

A branch class of a root union is paired with its branch node read
under the root's siblings: draft-07 applies every keyword beside the combinator to the same
instance the branch describes, so a field the branch inherits from the base is a fact its node
states and not one it added. A pair the payload generator cannot draw for still has to pass the
comparison, and names the shape that blocked the draw.

**The dual of that rule, for a node whose `type` is a LIST (added 2026-10-26).** A class cut
out of a type list is paired with its node read at **its own type word**, not at the whole list.
The union-branch rule above adds the root's siblings because the branch describes the same
instance the root does; this one subtracts the list's other words for the mirror reason — the
class describes one member of the union and the other members are carried by the field holding
it, not by this class.

Without it the same fact is counted twice and reported as a defect once. `core/delivery-metrics.json`
is the measured case: `/properties/quartile_data` states `type: ["object", "null"]`, the field
renders `DeliveryMetricsQuartileData | None`, and the ROOT pair passes because `_normalize`
folds the model's `anyOf: [{$ref}, {"type": "null"}]` back into the document's own list. The
nested class is then paired with the same node and reports `differs /type` — `object` against
`["object", "null"]` — for a fact the parent already carries and the comparison already graded.
The model is faithful at both pointers; only the pairing was wrong.

So a `null` member of a type list is the FIELD's fact, graded where the field is, and a member
class is graded against the shape it actually describes. Row `.20` found this by emitting new
documents into the three checks, reported it, and declined to invent the rule — which is why it
is here and not in a handler.

A check is exhaustive over the set of nodes it claims, or it does not exist. A check that
enumerates a subset reports on that subset only, and says so.

---

## 9. Mistakes to avoid

Each is one sentence and its reason.

- **Code nobody has written is an APPROXIMATION, never a refusal.** *This replaces "a refusal for
  code nobody has written is a DEFERRAL, never a verdict" on 2026-10-26.* The old rule separated
  two kinds of refusal because minting the permanent kind for unwritten code reports clearable
  work as finished. §2 now says unwritten code costs a declared widening and never a document, so
  the DEFERRAL has nothing left to be the kind of: the two kinds collapse to one, and the one
  that survives is the record's own (§7). The rule is the same rule one level stronger — do not
  charge a document for work we have not done — and the thing that must not be lost is what the
  deferral was carrying: *clearable* work stays visible, as the *ours* half of the approximation
  count, which ratchets down.
- **An approximation that narrows is not an approximation.** It is a model tighter than its
  document wearing a declaration, and §8's accepts draw is pointed at exactly that. Widen by
  another rung — to `Any` if nothing else carries it — rather than declaring the narrowing.
- **A declared approximation the model does not make is a stale excuse.** §8 reports it as
  *over-declared* and it is a defect, because a declaration that outlives its widening hides the
  next real gap at the same pointer.
- **Do not pin the approximation count.** It rises whenever the emitted set grows, which is the
  next rule in this list. Pin the four disagreement counts, which do not, and ratchet the *ours*
  split down.
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
  the walk is total, so this rule loses the type checker that used to enforce it — a handler had
  to answer the refusal branch — and what replaces it is that `approximate` is the one function a
  handler calls when it cannot render, reached by its own final arm. A handler that raises
  instead is the defect this rule is now about.
- **Do not decide one document's output by a census over the run.** A name, a shape or an
  import that depends on which other documents the run includes makes a one-document emission
  and a whole-bundle emission disagree about the same document; §2 names every constrained
  scalar from its constraint alone for this reason.
- **Do not decide a position the bundle does not hold from a view of it.** A shape that appears
  only in a canonicalised or otherwise rewritten copy of a document is the copy's, and a row
  deciding it decides nothing the bundle states; the document of record (§3) is what the tables
  decide over.
