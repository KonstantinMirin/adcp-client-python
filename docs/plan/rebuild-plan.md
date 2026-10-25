# The AdCP types SDK: what it is, and how it is built

The AdCP schema bundle is a directory of JSON Schema draft-07 documents. This describes how we
turn it into Pydantic models: what we produce, the principles that decide every case, how we walk
a document, what we emit, and how each keyword compiles. Where a keyword compiles to nothing, or
is refused, that is stated with the keyword.

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
from the import which document a class came from.

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

### Constraints bind to the type, not the field

A bound belongs to the thing it constrains:

```python
Annotated[int, Field(ge=1, le=100)]
```

not a `Field(ge=1)` sitting beside a bare `int` on one class. The constrained type is then
reusable: it nests into `list[...]`, into a mapping value, into a union branch, and into another
document's field, carrying its bound with it.

Three choices, in order of preference: a standard Pydantic type where one says exactly this
(`NonNegativeInt`); a named alias in `adcp.types.constraints` where the shape recurs
(`StrMinLen1`, `FloatGt0`, `NonEmptyList[T]`); the annotation written inline otherwise. An alias
in `constraints` names a *constraint*, never a concept — `NonEmptyList[T]`, not
`MediaBuyStatusList`.

*Why.* A bound written onto a field exists only at that field. The same bound reached through a
list, a mapping or a branch then has nowhere to live, and the usual repair is to put it on the
field holding the container — which constrains the wrong thing. On a union branch that repair is
actively wrong: the field also holds the other branch, so a bound there refuses values the
document accepts.

### Rules are after-validators, written once

A keyword that spans fields, or spans a collection, has no field-level annotation that can carry
it. Those become rules: an after-validator in `src/adcp/types/_runtime.py` reading a class-level
tuple the emitter writes. The families are `oneOf`/`anyOf` over `required`, `if`/`then`/`else`,
`dependencies`, `minProperties`/`maxProperties`, `uniqueItems`, `not`, and `contains`.

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

A composed class's `required` is the union of its own and every base's. Where composition makes
an inherited field required, the subclass redeclares that field with the base's type and no
default — and that is the only case in which an emitted class redeclares an inherited field. A
redeclaration that changes the type or adds a default is a build failure.

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

### A keyword we cannot express refuses the document

Where a position carries a keyword we have no compilation for, the document is refused by name,
pointer and keyword, and is not emitted. A partial model is worse than none: it would claim
conformance to a document it does not enforce.

A refusal states which kind it is. Either the obstruction is permanent — a property of the
document, of Pydantic, or of the pointer space — or the compilation for that position has not
been written yet. The two are counted separately and never summed.

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
shape. `Refusal` lives in the package every lowering imports, so any step can raise one without
an import cycle.

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

A root scalar is an alias, so it has no class to carry `strict_validate`; its module binds the
same validation as a module-level function over the same schema reference, so a class and an
alias cannot disagree about what their document accepts.

Two nodes with identical content emit one class. Two nodes with different content never do.

### Names

- **Root**: `pascal_case(title)`, acronyms kept. A missing or non-identifier title refuses.
- **Nested**: `pascal_case(property)` — `<Property>` for a property, `<Property>Item` for an array
  element, `<Property>Value` for a mapping value, `<Root><Key>` for a `definitions` entry. The
  module path already carries the document, so a nested name does not repeat it.
- **Union branch**: its own `title`; else the `const` it pins on the discriminating property; else
  its sorted `required` set.

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

The emitter writes two facts onto the base that are not recoverable at runtime: `_ROOT_REQUIRED`,
the fields the root requires as opposed to the ones that select a branch; and
`_branch_combinator()`, `anyOf` or `oneOf`, because a refusal has to name a JSON Schema keyword
and a document satisfying no branch fails each branch at field validation, where Pydantic reports
`missing`.

Branches subclass the base, so they do not exist while the base is built: the hook returns the
base's own schema then, and the declaring module calls `model_rebuild(force=True)` afterwards.

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

A union matching none of the three refuses, and what it refuses on is OVERLAP: a branch is never
chosen by trying each and keeping the first that validates, because overlapping branches make
that answer a property of declaration order rather than of the payload. Where nothing overlaps
there is no order to depend on, which is why the third source is a dispatch and not a relaxation.
A hand-written map per document is a fourth source and is refused: it is complete with respect to
itself, so a branch added upstream leaves it silently wrong.

---

## 5. How each keyword compiles

The draft-07 keywords the bundle uses. An answer is given per position where the positions differ.

### Structure

| keyword | compiles to |
| --- | --- |
| `type` | A scalar word → `str` / `int` / `float` / `bool`, unless a constrained type or `format` selects one. `object` with `properties` → a class; without → `dict[K, V]`. `array` → `list[X]`. `null` → `None`. A LIST of words → `A \| B`, each sibling keyword going to the one type word that can carry it. Absent → `Any`; absent beside `properties` → an object, where an enclosing node applies `type: object` to the same instance, and refused otherwise. |
| `properties` | A class with one field per key. PROP / ELEM / MAPV / DEF → a nested class. CONJ → fields of the composed class, merged by restatement: narrower wins, and neither narrowing refuses. ROOT beside a union → fields on the base, inherited by every branch. BRANCH → the branch class. RULE: under `if` → the values a `Match` clause tests, read only where `const` or `enum`; under `then` / `else` / `not` → nothing. |
| `required` | The named fields are required: no `\| None`, no default. Naming a property no node declares → refused, a presence rule with no field. CONJ → unioned into the composed class's `required`; a `required`-only conjunct → the overlay. ROOT beside a union → `_ROOT_REQUIRED` on the base. BRANCH → the branch class's requiredness, and the third of the branch-naming choices. RULE → a presence rule: `RequiredGroups`, `ForbiddenGroups` under `not`, the keys a `Match` clause tests under `if`, `ConditionalRequired` / `NegatedConditional` under `then` / `else`. `required: []` → nothing. |
| `definitions`, `$defs` | Nothing by itself: a bag of named subschemas. Each entry is declared on demand when a `$ref` names it, as the node's own kind, under `<Root><Key>`. |
| `$ref` | Another document's root → an IMPORT of that module's symbol; nothing of the target is copied. A fragment of another document → an import of a symbol the target declares. Local `#/…` → the entry decided on demand in this module; a cycle refuses. An annotation sibling → the sibling's description wins; a constraining sibling → refused. CONJ → a BASE. KEY → the key type. A BRANCH of a root union → a class with two bases; of a nested union → a member type. |

### Values

| keyword | compiles to |
| --- | --- |
| `const` | `Literal[value]`; the type word is not restated, since Pydantic renders it. A `str`, `bool` or `int` value; an object, array, `null` or float refuses. On a branch's property → also the second of the branch-naming choices. AT a branch node, pinning the whole branch → the branch is a scalar: a `Literal` member of a nested union, refused at a root union. RULE: under `if` → a `Match` clause's value; under `then` / `else` / `not` → nothing. |
| `enum` | A named node → `StrEnum` / `IntEnum`, base read off the members; `enumDescriptions` → member docstrings. ROOT → the enum with a module-level `strict_validate`. PROP → a nested enum. An untitled BRANCH of a root union → a `Literal` of the members. KEY → refused by name with the key set. RULE: under `if` → `Match` values; else nothing. Mixed member types, an empty list, or a duplicate member → refused. |
| `default` | PROP → the field's default; `None` is a default, absence is not. On a REQUIRED property → dropped and reported, because no rendering makes a field both required and defaulted. On a node that becomes an alias → no slot. |

### Strings

| keyword | compiles to |
| --- | --- |
| `pattern` | `pattern` on the type, as a named alias. On `format: uri` → selects the type instead, and the pattern stays with the schema half. ELEM / BRANCH → the alias as the element or member type. ROOT → the root alias over it. KEY → an annotated `str` key. RULE → nothing. The regex engine is derived per class, because a pattern using look-around needs Python's engine rather than Rust's. |
| `format` | Selects a TYPE where the document's draft asserts the format and a type is named: `date-time` → `AwareDatetime`, `date` → `datetime.date`, `uri` → a URL type chosen by `pattern`. Otherwise rides as `json_schema_extra={"format": …}` on the field. ELEM / MAPV with no type selected → a named alias carries it. BRANCH → the selected type as the member. A `uri` beside another string constraint → refused: a URL type carries none. |
| `minLength`, `maxLength` | `min_length` / `max_length` on the type, as a named alias. KEY → the key type, which Pydantic renders back as `propertyNames.minLength`. ELEM / MAPV → the alias inside the container. ROOT → the root alias. RULE → nothing. On a URL type → refused, not representable. |

### Numbers

| keyword | compiles to |
| --- | --- |
| `minimum`, `maximum` | `ge` / `le` on the type: a standard Pydantic type where one says exactly this, a named alias otherwise. ELEM / MAPV → the alias inside the container. BRANCH → the alias as the member type. RULE → nothing. |
| `exclusiveMinimum`, `exclusiveMaximum` | `gt` / `lt` on the type, **never `ge` / `le`**. The bundle distinguishes `minimum: 0` from `exclusiveMinimum: 0`, and the two differ on exactly one instance, so rendering either as the other makes a field accept a zero its document refuses or refuse a zero its document accepts. |
| `multipleOf` | Unused by the bundle. The first document to carry one refuses by name, rather than taking a rendering nothing has exercised. |

### Arrays

| keyword | compiles to |
| --- | --- |
| `items` | `list[X]`, X decided by the same walk and named where it needs a symbol. A list-valued `items` → refused: that is tuple validation. ROOT array → `RootModel[list[X]]`. RULE → nothing. |
| `minItems`, `maxItems` | `min_length` / `max_length` on the annotation of the **array's own type**, at every position. PROP → on the field. BRANCH → on the branch's own type, never on the field holding the union. MAPV / ELEM / DEF → the container's type must be named to carry it. `constraints` declares the recurring case once as `type NonEmptyList[T] = Annotated[list[T], Field(min_length=1)]`. `minItems: 0` states nothing. RULE → nothing. |
| `uniqueItems` | A `UniqueItems` rule on the class holding the array, plus `json_schema_extra={"uniqueItems": true}` on the field so it is graded, and the keyword is stripped off the array's own declaration. Where no class sits above the array → a `Distinct` after-validator on its own annotated type, beside the same `json_schema_extra`. |
| `contains` | An existential quantifier — `items` constrains every element, `contains` says at least one matches — and the model states the **predicate**, not a transcription of the subschema. A field position → an `AtLeastOne` after-validator on the array's own annotated type: `AtLeastOne(**{property: const})` where the subschema requires properties pinned to a const, `AtLeastOne(value)` where it is a bare `const` or a one-member `enum`. A RULE position → a `Match` MEMBERSHIP clause, `value in field`, and no validator. |

### Objects

| keyword | compiles to |
| --- | --- |
| `additionalProperties` | On a class: `false` → `forbid`; `true` → `allow`; typed → `allow` with a typed `__pydantic_extra__`; absent → `ignore`. On a mapping (no `properties`) → the VALUE type; `true` or `{}` → `Any`; `false` → refused, it admits only the empty object. Beside `patternProperties` → refused, two value schemas. CONJ → `true` is the identity and contributes nothing, `false` on any conjunct closes the composed object, and two typed ones intersect their value schemas; a typed conjunct beside a `true` one is a widening and refuses. `false` on an `allOf` overlay would reject the fields its sibling conjunct contributes, which is why `true` is the only value an overlay can carry. |
| `patternProperties` | A mapping whose KEY carries the pattern: `dict[Annotated[str, StringConstraints(pattern=…)], V]`, which Pydantic renders back as `patternProperties` — the document's own keyword. More than one pattern → refused: that is a value schema per key shape. Beside a non-`false` `additionalProperties` → refused. |
| `propertyNames` | The mapping's KEY type: a `$ref` → that type; `minLength` / `maxLength` → a length-bounded `str`; `pattern` → an annotated `str`; `enum` → refused by name with the key set; `anyOf` → a union of key types. At a RULE position → nothing on the model: a rule position constrains which keys a conditional *tests*, so there is no key type to annotate and no value to hang a validator on. |
| `minProperties`, `maxProperties` | On a class → a `PropertyCount` rule. `minProperties` is written only where `additionalProperties` is stated, because a dropped key would make the rule refuse what the document accepts; `maxProperties` needs no such gate, since a dropped key only lowers the count. On a mapping → `Field(min_length / max_length)` on the dict's type, because a `PropertyCount` rule counts declared fields and a dict has none. |
| `dependencies` | The list form → a `Dependencies` rule: if A is present, B is required. The schema form refuses by name on the first occurrence, rather than being skipped. |

### Combinators and conditionals

| keyword | compiles to |
| --- | --- |
| `allOf` | ROOT with no union beside → `$ref` conjuncts are BASES, inline conjuncts are fields and rules of this class. PROP / ELEM / DEF → the same reader at the node's own pointer. BRANCH → the branch class composes, with the union base first. ROOT beside a union → the bases reach every branch. CONJ → the same rule applied to the conjunct's own conjuncts. RULE: under `not` → single-group conjuncts merge into one group; else nothing. |
| `oneOf`, `anyOf` | Presence-only, every branch `required`-only → a `RequiredGroups` rule naming the combinator. Shapes at ROOT → the base plus one class per branch. Shapes nested → one type `A \| B`; a sibling beside it refuses. For `oneOf`, `A \| B` admits an instance satisfying two branches and the schema half enforces exclusivity. CONJ → one class per branch over the composed bases. KEY → a union of key types. A union whose branches differ only in their values → one class and a rule. RULE: under `not` → the union of the branches' groups; else nothing. |
| `if` | A `Match` clause list where it states `required` plus `properties` with `const` or `enum` values; otherwise nothing, and the schema half answers. With `then` / `else` → a rule on the nearest class. |
| `then`, `else` | `ConditionalRequired` / `NegatedConditional` from its `required` and a single-name `not`. Its `properties` → nothing on the model; the schema half narrows the value. |
| `not` | `not: {required: …}`, and `anyOf` / `allOf` of those → a `ForbiddenGroups` rule. Over a `const` or `enum` → a `NotValue` after-validator on the value's own annotated type. Any other shape → nothing on the model; the schema half answers and the ceiling is named. `not: {}` admits nothing, which the typeless `Any` carries. |

---

## 6. Keywords we admit and do not compile

None of these can constrain an instance, so none compiles to a type, a rule or a base. Each is
admitted **by name**. Several carry something anyway, and the table says what.

| keyword | what it does, or why nothing |
| --- | --- |
| `$schema` | Nothing on the class, but it selects the **validator** the schema half runs, and through it the format checkers a type may be selected for. The one annotation that decides a behaviour, and it decides it on the schema half. |
| `title` | ROOT → the symbol. BRANCH → the branch class's name. Nested → nothing: a nested node is named by its property or entry key. Its presence selects `StrEnum` over `Literal` for an enum node. Never rendered. |
| `description` | PROP → `Field(description=…)`. ROOT class → the docstring; ROOT alias → `Field(description=…)`; ROOT enum → the enum's docstring. ELEM / MAPV → the named alias carries it. A BRANCH that is a class → its docstring; a non-object branch of a nested union → its own annotated type. CONJ / RULE → nothing. A `$ref` sibling's description wins over the target's; a composed base's loses to the document's own. |
| `examples` | Nothing on the model. The accepts check replays every one: a payload the document refuses is a spec defect, reported by document and pointer; one the document accepts and the class refuses is ours. |
| `$comment` | Nothing. A note to a reader. |
| `readOnly`, `writeOnly` | Nothing. Pydantic can render them, but the SDK has one model per document and no read/write split for them to state. |
| `deprecated` | PROP → `Field(deprecated=True)`. ROOT and BRANCH → the class's `json_schema_extra`. A `false` → nothing. Rendered, so graded. |
| `enumDescriptions`, `x-enum-descriptions` | Member docstrings on the enumeration, keyed by the member's value. Two spellings of one keyword; both are read. |
| `enumMetadata` | Nothing: recovery and action metadata for a reader. The `enum` beside it has already closed the value set. |
| `notes` | Nothing: English sentences for a reader. |
| `discriminator` | Nothing on the class. It names a branch where that branch pins more than one `const`, and separately it **confirms** a dispatch key the branches already state — it does not establish one. A union whose branches pin a distinct const dispatches on that property whether or not the keyword is present, and a declared keyword the branches do not confirm is not a dispatch source. |
| the `x-` namespace | Nothing, and **still listed by name** — see below. |

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

## 7. Keywords we refuse

| keyword | why |
| --- | --- |
| `errorMessage` | An `ajv-errors` extension customising a validator's message. It has no Pydantic rendering, and a conjunct carrying one contributes nothing, so the drop is reported rather than silent. |
| `version`, `lastUpdated`, `vocabulary`, and the registry payload keys | A registry's own instance data sitting at a schema root: `_generated`, `_generatedAt`, `adcp_version`, `architecture`, `asset_types`, `baseUrl`, `extensions`, `governance`, `last_updated`, `mappings`, `prerelease`, `protocol_layers`, `published_version`, `stability`, `usage_notes`, `versioning`. Not annotations and not schema keywords, so admitting them by name would be admitting data as vocabulary. The documents carrying them are registries rather than schemas, and refusing them is how that shows up. |

A keyword in none of §5, §6 or §7 is one the bundle does not use. The first document to carry one
refuses by name, so a new keyword is loud rather than ignored.

---

## 8. How we know the output is right

Three checks, run once per emitted class against the schema document it names.

- **Accepts.** Draw a payload the document accepts and construct the class from it. A refusal here
  means the model is tighter than its document, which is the defect that matters.
- **Dump.** Serialize the instance and validate the dump against the document. A failure means we
  emit something our own schema refuses.
- **Compare.** Compare the class's `model_json_schema()` against the document, fact by fact. Three
  outcomes are distinguished: a fact the document states and the model does not (*missing*), a
  fact both state differently (*differs*), and a fact the model states and the document does not
  (*added*). The comparison is symmetric by construction, so neither direction can be silently
  unexamined.

Pydantic is deliberately less strict than JSON Schema, so a payload the *document* refuses tells
us nothing about the generated class on either route. There is therefore no "refuses" check on
the model; the equivalent check confirms the schema half is wired to the class at all.

Every class and alias the tree carries is paired with the schema node it names, and all three
checks run over that pairing. A pair the payload generator cannot draw for still has to pass the
comparison, and names the shape that blocked the draw.

A check is exhaustive over the set of nodes it claims, or it does not exist. A check that
enumerates a subset reports on that subset only, and says so.
